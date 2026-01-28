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

hubspot.extend(({ context, actions }) => (
  <CashFlowDashboard context={context} actions={actions} />
));

const CashFlowDashboard = ({ context, actions }) => {
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
          properties: ['dealname', 'amount', 'payment_expected_date', 'payment_received_date'],
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

  if (loading) return <LoadingSpinner label="Loading cash flow data..." />;
  if (error) return <Alert title="Error" variant="error">{error}</Alert>;

  const formatCurrency = (amount) => new Intl.NumberFormat('en-US', {
    style: 'currency', currency: 'USD', minimumFractionDigits: 0
  }).format(amount || 0);

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const todayStr = today.toISOString().split('T')[0];

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

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const getDaysOverdue = (dateStr) => {
    if (!dateStr) return 0;
    return Math.floor((today - new Date(dateStr)) / (1000 * 60 * 60 * 24));
  };

  return (
    <Flex direction="column" gap="large">
      <Text format={{ fontWeight: 'bold' }} variant="microcopy">CASH FLOW DASHBOARD</Text>

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

export default CashFlowDashboard;
