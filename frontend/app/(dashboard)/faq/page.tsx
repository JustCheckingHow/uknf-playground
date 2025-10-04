import { api } from '@/lib/api';
import { PageHeader } from '@/components/PageHeader';
import { Section } from '@/components/Section';

export const metadata = {
  title: 'FAQ | UKNF Communication Platform'
};

export default async function FAQPage() {
  const entries = await api.faq();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Questions and answers"
        description="Self-service knowledge base curated by UKNF subject matter experts."
      />
      <Section title="Frequently asked questions">
        <div className="space-y-4">
          {entries.length === 0 ? (
            <p className="text-sm text-slate-300">No FAQ entries available yet.</p>
          ) : (
            entries.map((entry) => (
              <article
                key={entry.id}
                className="rounded-lg border border-slate-200 bg-white p-4 transition-colors dark:border-slate-800 dark:bg-slate-900/30"
              >
                <h3 className="text-base font-semibold text-slate-900 dark:text-white">{entry.question}</h3>
                <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{entry.answer}</p>
                <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">
                  Last updated {new Date(entry.updatedAt).toLocaleDateString()}
                </p>
              </article>
            ))
          )}
        </div>
      </Section>
    </div>
  );
}
