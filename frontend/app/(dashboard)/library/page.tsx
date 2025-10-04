import { api } from '@/lib/api';
import { PageHeader } from '@/components/PageHeader';
import { Section } from '@/components/Section';
import { DataTable } from '@/components/DataTable';

export const metadata = {
  title: 'Library | UKNF Communication Platform'
};

export default async function LibraryPage() {
  const libraryItems = await api.library();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Knowledge library"
        description="Central repository for supervisory guidance, templates, and legal notices."
      />
      <Section title="Documents">
        <DataTable
          rows={libraryItems}
          columns={[
            { header: 'Title', accessor: (row) => row.title },
            { header: 'Category', accessor: (row) => row.category },
            { header: 'Updated', accessor: (row) => new Date(row.updatedAt).toLocaleDateString() },
            {
              header: 'Download',
              accessor: (row) => (
                <a
                  className="text-xs font-medium text-sky-600 transition-colors hover:text-sky-700 dark:text-sky-300 dark:hover:text-sky-200"
                  href={row.downloadUrl}
                  target="_blank"
                  rel="noreferrer"
                >
                  Download
                </a>
              )
            }
          ]}
          emptyState="No documents uploaded."
        />
      </Section>
    </div>
  );
}
