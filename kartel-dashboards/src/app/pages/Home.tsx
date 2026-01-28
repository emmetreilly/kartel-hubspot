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
  Button,
  Divider,
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
  <KartelDashboard context={context} actions={actions} />
));

const KartelDashboard = ({ context, actions }) => {
  const [activeTab, setActiveTab] = useState('executive');
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
            'dealname', 'amount', 'dealstage', 'pipeline', 'closedate',
            'hubspot_owner_id', 'deal_tier', 'spec_required', 'days_in_procurement',
            'payment_expected_date', 'payment_received_date',
            'phase_3_start_date', 'renewal_date'
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

  const formatCurrency = (amount) => new Intl.NumberFormat('en-US', {
    style: 'currency', currency: 'USD', minimumFractionDigits: 0
  }).format(amount || 0);

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  if (loading) {
    return (
      <Flex direction="column" align="center" gap="medium">
        <LoadingSpinner label="Loading Kartel Dashboards..." />
      </Flex>
    );
  }

  if (error) {
    return <Alert title="Error" variant="error">{error}</Alert>;
  }

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const todayStr = today.toISOString().split('T')[0];

  return (
    <Flex direction="column" gap="large">
      <Text format={{ fontWeight: 'bold' }}>KARTEL DASHBOARDS</Text>

      <Flex direction="row" gap="small">
        <Button
          variant={activeTab === 'executive' ? 'primary' : 'secondary'}
          onClick={() => setActiveTab('executive')}
        >
          Executive
        </Button>
        <Button
          variant={activeTab === 'sales' ? 'primary' : 'secondary'}
          onClick={() => setActiveTab('sales')}
        >
          Sales
        </Button>
        <Button
          variant={activeTab === 'cashflow' ? 'primary' : 'secondary'}
          onClick={() => setActiveTab('cashflow')}
        >
          Cash Flow
        </Button>
        <Button
          variant={activeTab === 'operations' ? 'primary' : 'secondary'}
          onClick={() => setActiveTab('operations')}
        >
          Operations
        </Button>
      </Flex>

      <Divider />

      {activeTab === 'executive' && (
        <ExecutiveView deals={deals} formatCurrency={formatCurrency} />
      )}
      {activeTab === 'sales' && (
        <SalesView deals={deals} formatCurrency={formatCurrency} />
      )}
      {activeTab === 'cashflow' && (
        <CashFlowView deals={deals} formatCurrency={formatCurrency} formatDate={formatDate} todayStr={todayStr} today={today} />
      )}
      {activeTab === 'operations' && (
        <OperationsView deals={deals} formatCurrency={formatCurrency} formatDate={formatDate} todayStr={todayStr} today={today} />
      )}
    </Flex>
  );
};

const ExecutiveView = ({ deals, formatCurrency }) => {
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

  return (
    <Flex direction="column" gap="large">
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
            <Tag key={tier}>{tier}: {formatCurrency(total)}</Tag>
          ))}
        </Flex>
      </Flex>

      <Flex direction="column" gap="small">
        <Text format={{ fontWeight: 'bold' }}>Deals by Pipeline</Text>
        <Flex direction="row" gap="small" wrap="wrap">
          {Object.entries(pipelineCounts).map(([pipeline, count]) => (
            <Tag key={pipeline} variant="default">{pipeline}: {count}</Tag>
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

const SalesView = ({ deals, formatCurrency }) => {
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

const CashFlowView = ({ deals, formatCurrency, formatDate, todayStr, today }) => {
  const future30 = new Date(today);
  future30.setDate(future30.getDate() + 30);
  const future30Str = future30.toISOString().split('T')[0];

  const future90 = new Date(today);
  future90.setDate(future90.getDate() + 90);
  const future90Str = future90.toISOString().split('T')[0];

  const expectedPayments = deals.filter(d =>
    d.payment_expected_date && !d.payment_received_date
  ).sort((a, b) => (a.payment_expected_date || '').localeCompare(b.payment_expected_date || ''));

  const overduePayments = expectedPayments.filter(d => d.payment_expected_date < todayStr);
  const dueThisMonth = expectedPayments.filter(d =>
    d.payment_expected_date >= todayStr && d.payment_expected_date <= future30Str
  );
  const forecast90Day = expectedPayments.filter(d =>
    d.payment_expected_date >= todayStr && d.payment_expected_date <= future90Str
  );

  const totalExpected = expectedPayments.reduce((s, d) => s + (parseFloat(d.amount) || 0), 0);
  const totalOverdue = overduePayments.reduce((s, d) => s + (parseFloat(d.amount) || 0), 0);
  const totalDueThisMonth = dueThisMonth.reduce((s, d) => s + (parseFloat(d.amount) || 0), 0);
  const total90Day = forecast90Day.reduce((s, d) => s + (parseFloat(d.amount) || 0), 0);

  const getDaysOverdue = (dateStr) => {
    if (!dateStr) return 0;
    return Math.floor((today - new Date(dateStr)) / (1000 * 60 * 60 * 24));
  };

  return (
    <Flex direction="column" gap="large">
      <Statistics>
        <StatisticsItem label="Total Outstanding" number={formatCurrency(totalExpected)} />
        <StatisticsItem label="Overdue" number={formatCurrency(totalOverdue)} />
        <StatisticsItem label="Due (30 Days)" number={formatCurrency(totalDueThisMonth)} />
        <StatisticsItem label="90-Day Forecast" number={formatCurrency(total90Day)} />
      </Statistics>

      {overduePayments.length > 0 && (
        <Alert title={`${overduePayments.length} Overdue Payments`} variant="danger">
          Total: {formatCurrency(totalOverdue)} needs immediate follow-up
        </Alert>
      )}

      {overduePayments.length > 0 && (
        <Flex direction="column" gap="small">
          <Text format={{ fontWeight: 'bold' }}>Overdue Payments</Text>
          <Table>
            <TableHead>
              <TableRow>
                <TableHeader>Deal</TableHeader>
                <TableHeader>Amount</TableHeader>
                <TableHeader>Was Due</TableHeader>
                <TableHeader>Days Overdue</TableHeader>
              </TableRow>
            </TableHead>
            <TableBody>
              {overduePayments.map((deal) => (
                <TableRow key={deal.hs_object_id}>
                  <TableCell>{deal.dealname}</TableCell>
                  <TableCell>{formatCurrency(deal.amount)}</TableCell>
                  <TableCell>{formatDate(deal.payment_expected_date)}</TableCell>
                  <TableCell><Tag variant="error">{getDaysOverdue(deal.payment_expected_date)} days</Tag></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Flex>
      )}

      <Flex direction="column" gap="small">
        <Text format={{ fontWeight: 'bold' }}>Due Next 30 Days ({formatCurrency(totalDueThisMonth)})</Text>
        {dueThisMonth.length > 0 ? (
          <Table>
            <TableHead>
              <TableRow>
                <TableHeader>Deal</TableHeader>
                <TableHeader>Amount</TableHeader>
                <TableHeader>Due Date</TableHeader>
              </TableRow>
            </TableHead>
            <TableBody>
              {dueThisMonth.map((deal) => (
                <TableRow key={deal.hs_object_id}>
                  <TableCell>{deal.dealname}</TableCell>
                  <TableCell>{formatCurrency(deal.amount)}</TableCell>
                  <TableCell>{formatDate(deal.payment_expected_date)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <Text>No payments expected in the next 30 days</Text>
        )}
      </Flex>

      <Flex direction="column" gap="small">
        <Text format={{ fontWeight: 'bold' }}>90-Day Forecast by Month</Text>
        <Flex direction="row" gap="medium" wrap="wrap">
          {(() => {
            const byMonth = {};
            forecast90Day.forEach(d => {
              const month = (d.payment_expected_date || '').substring(0, 7);
              if (month) byMonth[month] = (byMonth[month] || 0) + (parseFloat(d.amount) || 0);
            });
            return Object.entries(byMonth).map(([month, total]) => (
              <Flex key={month} direction="column" gap="extra-small">
                <Text format={{ fontWeight: 'bold' }}>{month}</Text>
                <Tag variant="success">{formatCurrency(total)}</Tag>
              </Flex>
            ));
          })()}
        </Flex>
      </Flex>
    </Flex>
  );
};

const OperationsView = ({ deals, formatCurrency, formatDate, todayStr, today }) => {
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

  const getDaysUntil = (dateStr) => {
    if (!dateStr) return null;
    return Math.ceil((new Date(dateStr) - today) / (1000 * 60 * 60 * 24));
  };

  return (
    <Flex direction="column" gap="large">
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

export default KartelDashboard;
