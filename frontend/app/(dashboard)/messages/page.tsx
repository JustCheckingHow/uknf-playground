import { api } from '@/lib/api';
import { PageHeader } from '@/components/PageHeader';
import { Section } from '@/components/Section';
import { DataTable } from '@/components/DataTable';

export const metadata = {
  title: 'Messages | UKNF Communication Platform'
};

export default async function MessagesPage() {
  const messages = await api.messages();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Secure messages"
        description="Encrypted correspondence channel with full audit history."
      />
      <Section
        title="Recent conversations"
        description="Message retention policies enforce seven-year storage per regulatory obligations."
      >
        <DataTable
          rows={messages}
          columns={[
            { header: 'Subject', accessor: (row) => row.subject },
            { header: 'Counterpart', accessor: (row) => row.counterpart },
            { header: 'Last activity', accessor: (row) => new Date(row.updatedAt).toLocaleString() }
          ]}
          emptyState="No conversations yet."
        />
      </Section>
    </div>
  );
}
