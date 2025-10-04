import { api } from '@/lib/api';
import { PageHeader } from '@/components/PageHeader';
import { Section } from '@/components/Section';
import { DataTable } from '@/components/DataTable';
import { StatusPill } from '@/components/StatusPill';

export const metadata = {
  title: 'Cases | UKNF Communication Platform'
};

export default async function CasesPage() {
  const cases = await api.cases();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Regulatory matters"
        description="Case management view consolidates correspondence, attachments, and workflow states."
      />
      <Section title="Open cases">
        <DataTable
          rows={cases}
          columns={[
            { header: 'Reference', accessor: (row) => row.reference },
            { header: 'Topic', accessor: (row) => row.topic },
            { header: 'Status', accessor: (row) => <StatusPill status={row.status} /> },
            { header: 'Updated', accessor: (row) => new Date(row.updatedAt).toLocaleString() }
          ]}
          emptyState="No active cases."
        />
      </Section>
    </div>
  );
}
