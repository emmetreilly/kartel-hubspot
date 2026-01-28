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

const PIPELINES = {
  client_delivery: '1880222399',
  reengagement: '1880222400',
};

const DELIVERY_STAGES = {
  phase_1_scoping: 'Phase 1: Scoping',
  phase_2_build: 'Phase 2: Build',
  phase_3_pending: 'Phase 3: Pending',
  phase_3_active: 'Phase 3: Active',
  churned: 'Churned',
  renewed: 'Renewed',
};

const REENGAGEMENT_STAGES = {
  identified: 'Identified',
  outreach: 'Outreach',
  qualified: 'Qualified',
  scoping: 'Scoping',
  converted: 'Converted',
  not_now: 'Not Now',
};

hubspot.extend(({ context, actions }) => (
  <OperationsDashboard context={context} actions={actions} />
));

const OperationsDashboard = ({ context, actions }) => {
  const [deals, setDeals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => { fetchDeals(); }, []);

  const fetchDeals = async () => {
    try {
      const response = await hubspot.fetch('/crm/v3/objects/deals/search', {
        method: 'POST',
        body: {
          limit: 100,
          properties: ['dealname', 'amount', 'dealstage', 'pipeline', 'phase_3_start_date', 'renewal_date'],
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

  if (loading) return <LoadingSpinner label="Loading operations data..." />;
  if (error) return <Alert title="Error" variant="error">{error}</Alert>;

  const formatCurrency = (amount) => new Intl.NumberFormat('en-US', {
    style: 'currency', currency: 'USD', minimumFractionDigits: 0
  }).format(amount || 0);

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const todayStr = today.toISOString().split('T')[0];

  const future60 = new Date(today);
  future60.setDate(future60.getDate() + 60);
  const future60Str = future60.toISOString().split('T')[0];

  const future90 = new Date(today);
  future90.setDate(future90.getDate() + 90);
  const future90Str = future90.toISOString().split('T')[0];

  const deliveryDeals = deals.filter(d => d.pipeline === PIPELINES.client_delivery);
  const reengagementDeals = deals.filter(d => d.pipeline === PIPELINES.reengagement);

  const phase3Upcoming = deals.filter(d => {
    const date = d.phase_3_start_date;
    return date && date >= todayStr && date <= future60Str;
  }).sort((a, b) => (a.phase_3_start_date || '').localeCompare(b.phase_3_start_date || ''));

  const renewalsUpcoming = deals.filter(d => {
    const date = d.renewal_date;
    return date && date >= todayStr && date <= future90Str;
  }).sort((a, b) => (a.renewal_date || '').localeCompare(b.renewal_date || ''));

  const activeClients = deliveryDeals.filter(d =>
    d.dealstage === 'phase_3_active' || (d.dealstage || '').includes('active')
  );

  const deliveryStageCounts = {};
  deliveryDeals.forEach(d => {
    const stage = d.dealstage || 'unknown';
    deliveryStageCounts[stage] = (deliveryStageCounts[stage] || 0) + 1;
  });

  const reengagementStageCounts = {};
  reengagementDeals.forEach(d => {
    const stage = d.dealstage || 'unknown';
    reengagementStageCounts[stage] = (reengagementStageCounts[stage] || 0) + 1;
  });

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const getDaysUntil = (dateStr) => {
    if (!dateStr) return null;
    return Math.ceil((new Date(dateStr) - today) / (1000 * 60 * 60 * 24));
  };

  return (
    <Flex direction="column" gap="large">
      <Text format={{ fontWeight: 'bold' }} variant="microcopy">OPERATIONS DASHBOARD</Text>

      <Statistics>
        <StatisticsItem label="Active Clients" number={activeClients.length.toString()} />
        <StatisticsItem label="In Delivery" number={deliveryDeals.length.toString()} />
        <StatisticsItem label="Re-engagement" number={reengagementDeals.length.toString()} />
        <StatisticsItem label="Renewals (90d)" number={renewalsUpcoming.length.toString()} />
      </Statistics>

      {phase3Upcoming.length > 0 && (
        <Alert title={`${phase3Upcoming.length} Phase III Starting Soon`} variant="info">
          Review clients approaching Phase III commitment
        </Alert>
      )}

      {renewalsUpcoming.length > 0 && (
        <Alert title={`${renewalsUpcoming.length} Renewals in 90 Days`} variant="warning">
          Schedule renewal conversations
        </Alert>
      )}

      <Flex direction="column" gap="small">
        <Text format={{ fontWeight: 'bold' }}>Client Delivery Pipeline</Text>
        <Flex direction="row" gap="small" wrap="wrap">
          {Object.entries(deliveryStageCounts).map(([stage, count]) => (
            <Tag key={stage} variant={stage.includes('active') ? 'success' : 'default'}>
              {DELIVERY_STAGES[stage] || stage}: {count}
            </Tag>
          ))}
        </Flex>
      </Flex>

      <Flex direction="column" gap="small">
        <Text format={{ fontWeight: 'bold' }}>Phase III Starting (Next 60 Days)</Text>
        {phase3Upcoming.length > 0 ? (
          <Table>
            <TableHead>
              <TableRow>
                <TableHeader>Client</TableHeader>
                <TableHeader>Phase III Date</TableHeader>
                <TableHeader>Days Until</TableHeader>
                <TableHeader>Value</TableHeader>
              </TableRow>
            </TableHead>
            <TableBody>
              {phase3Upcoming.map((deal) => (
                <TableRow key={deal.hs_object_id}>
                  <TableCell>{deal.dealname}</TableCell>
                  <TableCell>{formatDate(deal.phase_3_start_date)}</TableCell>
                  <TableCell><Tag variant="info">{getDaysUntil(deal.phase_3_start_date)} days</Tag></TableCell>
                  <TableCell>{formatCurrency(deal.amount)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <Text>No Phase III starts in the next 60 days</Text>
        )}
      </Flex>

      <Flex direction="column" gap="small">
        <Text format={{ fontWeight: 'bold' }}>Renewal Calendar (Next 90 Days)</Text>
        {renewalsUpcoming.length > 0 ? (
          <Table>
            <TableHead>
              <TableRow>
                <TableHeader>Client</TableHeader>
                <TableHeader>Renewal Date</TableHeader>
                <TableHeader>Days Until</TableHeader>
                <TableHeader>Value</TableHeader>
              </TableRow>
            </TableHead>
            <TableBody>
              {renewalsUpcoming.map((deal) => {
                const daysUntil = getDaysUntil(deal.renewal_date);
                return (
                  <TableRow key={deal.hs_object_id}>
                    <TableCell>{deal.dealname}</TableCell>
                    <TableCell>{formatDate(deal.renewal_date)}</TableCell>
                    <TableCell><Tag variant={daysUntil < 30 ? 'warning' : 'default'}>{daysUntil} days</Tag></TableCell>
                    <TableCell>{formatCurrency(deal.amount)}</TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        ) : (
          <Text>No renewals in the next 90 days</Text>
        )}
      </Flex>

      <Flex direction="column" gap="small">
        <Text format={{ fontWeight: 'bold' }}>Re-engagement Pipeline</Text>
        {reengagementDeals.length > 0 ? (
          <Flex direction="row" gap="small" wrap="wrap">
            {Object.entries(reengagementStageCounts).map(([stage, count]) => (
              <Tag key={stage} variant={stage === 'converted' ? 'success' : 'default'}>
                {REENGAGEMENT_STAGES[stage] || stage}: {count}
              </Tag>
            ))}
          </Flex>
        ) : (
          <Text>No active re-engagement opportunities</Text>
        )}
      </Flex>
    </Flex>
  );
};

export default OperationsDashboard;
