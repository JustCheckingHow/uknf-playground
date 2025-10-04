import { api } from '@/lib/api';
import { PageHeader } from '@/components/PageHeader';
import { Section } from '@/components/Section';
import { DataTable } from '@/components/DataTable';

export const metadata = {
  title: 'Entities | UKNF Communication Platform'
};

export default async function EntitiesPage() {
  const entities = await api.entities();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Supervised entities"
        description="Entity master data with governance for updates and approvals."
      />
      <Section title="Directory">
        <DataTable
          rows={entities}
          columns={[
            { header: 'Name', accessor: (row) => row.name },
            { header: 'Category', accessor: (row) => row.category },
            { header: 'KRS', accessor: (row) => row.krs ?? '—' },
            { header: 'Updated', accessor: (row) => new Date(row.updatedAt).toLocaleDateString() }
          ]}
          emptyState="No entities available."
        />
      </Section>
    </div>
  );
}
