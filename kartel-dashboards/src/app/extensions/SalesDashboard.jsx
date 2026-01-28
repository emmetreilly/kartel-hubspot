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
  Alert,
  LoadingSpinner,
  hubspot,
} from '@hubspot/ui-extensions';

const STAGE_NAMES = {
  '2978915058': 'Discovery',
  '2978915059': 'Product Scope',
  '2978915060': 'Budget Scope',
  '2978915061': 'Proposal',
  '2978915062': 'Negotiation',
  '2978915063': 'Procurement',
  '2978915064': 'Closed Won',
};

hubspot.extend(({ context, actions }) => (
  <SalesDashboard context={context} actions={actions} />
));

const SalesDashboard = ({ context, actions }) => {
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
            'deal_tier', 'spec_required', 'days_in_procurement'
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

  if (loading) return <LoadingSpinner label="Loading sales data..." />;
  if (error) return <Alert title="Error" variant="error">{error}</Alert>;

  const formatCurrency = (amount) => new Intl.NumberFormat('en-US', {
    style: 'currency', currency: 'USD', minimumFractionDigits: 0
  }).format(amount || 0);

  const activeDeals = deals.filter(d =>
    !['closedwon', 'closedlost', '2978915064', '2978915065'].includes(d.dealstage)
  );

  const actionDeals = activeDeals.filter(d => {
    const inBudgetScope = d.dealstage === '2978915060';
    const specDelivered = d.spec_required === 'delivered';
    const inProcurement = d.dealstage === '2978915063';
    const daysInProcurement = parseInt(d.days_in_procurement) || 0;
    return (inBudgetScope && specDelivered) || (inProcurement && daysInProcurement > 30);
  });

  const stageBreakdown = {};
  activeDeals.forEach(d => {
    const stage = STAGE_NAMES[d.dealstage] || d.dealstage;
    if (!stageBreakdown[stage]) stageBreakdown[stage] = { count: 0, amount: 0 };
    stageBreakdown[stage].count++;
    stageBreakdown[stage].amount += parseFloat(d.amount) || 0;
  });

  const specStatus = { yes: 0, no: 0, in_progress: 0, delivered: 0, none: 0 };
  activeDeals.forEach(d => {
    const status = d.spec_required || 'none';
    specStatus[status] = (specStatus[status] || 0) + 1;
  });

  return (
    <Flex direction="column" gap="large">
      <Text format={{ fontWeight: 'bold' }} variant="microcopy">SALES DASHBOARD</Text>

      <Statistics>
        <StatisticsItem label="Active Deals" number={activeDeals.length.toString()} />
        <StatisticsItem label="Total Value" number={formatCurrency(activeDeals.reduce((s, d) => s + (parseFloat(d.amount) || 0), 0))} />
        <StatisticsItem label="Needs Action" number={actionDeals.length.toString()} />
      </Statistics>

      {actionDeals.length > 0 && (
        <Flex direction="column" gap="small">
          <Text format={{ fontWeight: 'bold' }}>Deals Requiring Action</Text>
          {actionDeals.map((deal) => (
            <Alert key={deal.hs_object_id} title={deal.dealname} variant="warning">
              {deal.spec_required === 'delivered' && deal.dealstage === '2978915060'
                ? 'GO/NO-GO: Spec delivered, in Budget Scope. Move to Proposal or close.'
                : `In Procurement ${deal.days_in_procurement || '30+'} days. Follow up on signature.`}
            </Alert>
          ))}
        </Flex>
      )}

      <Flex direction="column" gap="small">
        <Text format={{ fontWeight: 'bold' }}>Active Deals</Text>
        <Table>
          <TableHead>
            <TableRow>
              <TableHeader>Deal</TableHeader>
              <TableHeader>Amount</TableHeader>
              <TableHeader>Stage</TableHeader>
              <TableHeader>Spec</TableHeader>
              <TableHeader>Tier</TableHeader>
            </TableRow>
          </TableHead>
          <TableBody>
            {activeDeals.slice(0, 15).map((deal) => (
              <TableRow key={deal.hs_object_id}>
                <TableCell>{deal.dealname}</TableCell>
                <TableCell>{formatCurrency(deal.amount)}</TableCell>
                <TableCell>{STAGE_NAMES[deal.dealstage] || deal.dealstage}</TableCell>
                <TableCell>{deal.spec_required ? <Tag variant={deal.spec_required === 'delivered' ? 'success' : 'default'}>{deal.spec_required}</Tag> : '-'}</TableCell>
                <TableCell>{deal.deal_tier || '-'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Flex>

      <Flex direction="column" gap="small">
        <Text format={{ fontWeight: 'bold' }}>By Stage</Text>
        <Flex direction="row" gap="small" wrap="wrap">
          {Object.entries(stageBreakdown).map(([stage, data]) => (
            <Tag key={stage}>{stage}: {data.count} ({formatCurrency(data.amount)})</Tag>
          ))}
        </Flex>
      </Flex>

      <Flex direction="column" gap="small">
        <Text format={{ fontWeight: 'bold' }}>Spec Status</Text>
        <Flex direction="row" gap="small" wrap="wrap">
          {Object.entries(specStatus).filter(([_, count]) => count > 0).map(([status, count]) => (
            <Tag key={status} variant={status === 'delivered' ? 'success' : 'default'}>{status}: {count}</Tag>
          ))}
        </Flex>
      </Flex>
    </Flex>
  );
};

export default SalesDashboard;
