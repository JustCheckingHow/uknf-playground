using System.Globalization;
using UKNF.Backend.Models.Communication;

namespace UKNF.Backend.Services.Communication;

public class LibraryService
{
    private static readonly LibraryRecord[] SeedItems =
    {
        new(
            "lib-1",
            "UKNF Reporting Manual 2025",
            "Guidelines",
            DateTimeOffset.Parse("2025-01-15T00:00:00Z", CultureInfo.InvariantCulture),
            "https://example.com/files/reporting-manual-2025.pdf"
        ),
        new(
            "lib-2",
            "Cyber incident notification template",
            "Templates",
            DateTimeOffset.Parse("2025-02-05T00:00:00Z", CultureInfo.InvariantCulture),
            "https://example.com/files/cyber-incident-template.docx"
        )
    };

    public IEnumerable<LibraryRecord> GetAll() => SeedItems;
}
