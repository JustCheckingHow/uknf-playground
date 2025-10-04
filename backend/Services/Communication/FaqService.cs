using System.Globalization;
using UKNF.Backend.Models.Communication;

namespace UKNF.Backend.Services.Communication;

public class FaqService
{
    private static readonly FaqRecord[] SeedItems =
    {
        new(
            "faq-1",
            "How long do we keep regulatory correspondence?",
            "All case-related communications are retained for a minimum of seven years in compliance with sector regulations.",
            DateTimeOffset.Parse("2025-03-12T00:00:00Z", CultureInfo.InvariantCulture)
        ),
        new(
            "faq-2",
            "Can we submit corrections after validation errors?",
            "Yes. Upload a corrected file referencing the original submission ID. The validation engine tracks versions automatically.",
            DateTimeOffset.Parse("2025-03-08T00:00:00Z", CultureInfo.InvariantCulture)
        )
    };

    public IEnumerable<FaqRecord> GetAll() => SeedItems;
}
