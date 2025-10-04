import { api } from '@/lib/api';
import { PageHeader } from '@/components/PageHeader';
import { Section } from '@/components/Section';
import { DataTable } from '@/components/DataTable';
import { StatusPill } from '@/components/StatusPill';

export const metadata = {
  title: 'Reports | UKNF Communication Platform'
};

export default async function ReportsPage() {
  const reports = await api.reports();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Regulatory Reports"
        description="Track the lifecycle of submitted supervision reports with validation feedback."
      />
      <Section
        title="Recent submissions"
        description="Statuses align with the UKNF validation process, including technical and manual review outcomes."
      >
        <DataTable
          rows={reports}
          columns={[
            { header: 'Report', accessor: (row) => row.name },
            { header: 'Period', accessor: (row) => row.period },
            { header: 'Status', accessor: (row) => <StatusPill status={row.status} /> },
            { header: 'Submitted', accessor: (row) => new Date(row.submittedAt).toLocaleString() }
          ]}
          emptyState="No reports submitted in this environment."
        />
      </Section>
    </div>
  );
}
