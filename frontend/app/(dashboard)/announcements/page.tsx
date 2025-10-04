import { api } from '@/lib/api';
import { PageHeader } from '@/components/PageHeader';
import { Section } from '@/components/Section';
import { DataTable } from '@/components/DataTable';

export const metadata = {
  title: 'Announcements | UKNF Communication Platform'
};

export default async function AnnouncementsPage() {
  const announcements = await api.announcements();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Announcements"
        description="Official communications with acknowledgement tracking and audience segmentation."
      />
      <Section title="Published notices">
        <DataTable
          rows={announcements}
          columns={[
            { header: 'Title', accessor: (row) => row.title },
            { header: 'Audience', accessor: (row) => row.targetAudience },
            {
              header: 'Acknowledged',
              accessor: (row) => `${Math.round(row.acknowledgementRate * 100)}%`
            },
            { header: 'Published', accessor: (row) => new Date(row.publishedAt).toLocaleString() }
          ]}
          emptyState="No announcements published."
        />
      </Section>
    </div>
  );
}
