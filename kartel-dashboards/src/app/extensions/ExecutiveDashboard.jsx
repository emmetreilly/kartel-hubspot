import React, { useState, useEffect } from 'react';
import {
  Flex,
  Text,
  Statistics,
  StatisticsItem,
  Table,
  TableHead,
  TableRow,
  TableHeader,
  TableBody,
  TableCell,
  Tag,
  LoadingSpinner,
  hubspot,
} from '@hubspot/ui-extensions';

const PIPELINES = {
  enterprise: '1880222397',
  smb: '1880222398',
  client_delivery: '1880222399',
  reengagement: '1880222400',
};

const STAGE_NAMES = {
  '2978915058': 'Discovery',
  '2978915059': 'Product Scope',
  '2978915060': 'Budget Scope',
  '2978915061': 'Proposal',
  '2978915062': 'Negotiation',
  '2978915063': 'Procurement',
  '2978915064': 'Closed Won',
  '2978915065': 'Closed Lost',
};

hubspot.extend(({ context, actions }) => (
  <ExecutiveDashboard context={context} actions={actions} />
));

const ExecutiveDashboard = ({ context, actions }) => {
  const [deals, setDeals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDeals();
  }, []);

  const fetchDeals = async () => {
    try {
      const response = await hubspot.fetch('/crm/v3/objects/deals/search', {
        method: 'POST',
        body: {
          limit: 100,
          properties: [
            'dealname', 'amount', 'dealstage', 'pipeline',
            'closedate', 'hubspot_owner_id', 'deal_tier'
          ],
          sorts: [{ propertyName: 'amount', direction: 'DESCENDING' }],
        },
      });

      if (response.ok) {
        const data = await response.json();
        setDeals(data.results?.map(d => ({ hs_object_id: d.id, ...d.properties })) || []);
      } else {
        setError('Failed to fetch deals');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Flex direction="column" align="center" gap="medium">
        <LoadingSpinner label="Loading dashboard data..." />
      </Flex>
    );
  }

  if (error) {
    return (
      <Flex direction="column" gap="small">
        <Text format={{ fontWeight: 'bold' }}>Error loading data</Text>
        <Text>{error}</Text>
      </Flex>
    );
  }

  const openDeals = deals.filter(d =>
    !['closedwon', 'closedlost', '2978915064', '2978915065'].includes(d.dealstage)
  );
  const wonDeals = deals.filter(d =>
    ['closedwon', '2978915064'].includes(d.dealstage)
  );
  const lostDeals = deals.filter(d =>
    ['closedlost', '2978915065'].includes(d.dealstage)
  );

  const totalPipeline = openDeals.reduce((sum, d) => sum + (parseFloat(d.amount) || 0), 0);
  const totalWon = wonDeals.reduce((sum, d) => sum + (parseFloat(d.amount) || 0), 0);
  const winRate = (wonDeals.length + lostDeals.length) > 0
    ? Math.round((wonDeals.length / (wonDeals.length + lostDeals.length)) * 100)
    : 0;

  const tierTotals = {};
  openDeals.forEach(d => {
    const tier = d.deal_tier || 'Unassigned';
    tierTotals[tier] = (tierTotals[tier] || 0) + (parseFloat(d.amount) || 0);
  });

  const pipelineCounts = {};
  openDeals.forEach(d => {
    const pipeline = Object.entries(PIPELINES).find(([_, id]) => id === d.pipeline)?.[0] || 'other';
    pipelineCounts[pipeline] = (pipelineCounts[pipeline] || 0) + 1;
  });

  const topDeals = [...openDeals]
    .sort((a, b) => (parseFloat(b.amount) || 0) - (parseFloat(a.amount) || 0))
    .slice(0, 5);

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount || 0);
  };

  return (
    <Flex direction="column" gap="large">
      <Text format={{ fontWeight: 'bold' }} variant="microcopy">
        EXECUTIVE DASHBOARD
      </Text>

      <Statistics>
        <StatisticsItem label="Total Pipeline" number={formatCurrency(totalPipeline)} />
        <StatisticsItem label="Open Deals" number={openDeals.length.toString()} />
        <StatisticsItem label="Total Won" number={formatCurrency(totalWon)} />
        <StatisticsItem label="Win Rate" number={`${winRate}%`} />
      </Statistics>

      <Flex direction="column" gap="small">
        <Text format={{ fontWeight: 'bold' }}>Pipeline by Deal Tier</Text>
        <Flex direction="row" gap="small" wrap="wrap">
          {Object.entries(tierTotals).map(([tier, total]) => (
            <Tag key={tier}>
              {tier}: {formatCurrency(total)}
            </Tag>
          ))}
        </Flex>
      </Flex>

      <Flex direction="column" gap="small">
        <Text format={{ fontWeight: 'bold' }}>Deals by Pipeline</Text>
        <Flex direction="row" gap="small" wrap="wrap">
          {Object.entries(pipelineCounts).map(([pipeline, count]) => (
            <Tag key={pipeline} variant="default">
              {pipeline}: {count}
            </Tag>
          ))}
        </Flex>
      </Flex>

      <Flex direction="column" gap="small">
        <Text format={{ fontWeight: 'bold' }}>Top 5 Deals</Text>
        <Table>
          <TableHead>
            <TableRow>
              <TableHeader>Deal Name</TableHeader>
              <TableHeader>Amount</TableHeader>
              <TableHeader>Stage</TableHeader>
              <TableHeader>Tier</TableHeader>
            </TableRow>
          </TableHead>
          <TableBody>
            {topDeals.map((deal) => (
              <TableRow key={deal.hs_object_id}>
                <TableCell>{deal.dealname}</TableCell>
                <TableCell>{formatCurrency(deal.amount)}</TableCell>
                <TableCell>{STAGE_NAMES[deal.dealstage] || deal.dealstage}</TableCell>
                <TableCell>{deal.deal_tier || '-'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Flex>
    </Flex>
  );
};

export default ExecutiveDashboard;
