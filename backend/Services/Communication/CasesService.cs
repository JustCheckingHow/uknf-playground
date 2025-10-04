using System.Globalization;
using UKNF.Backend.Models.Communication;

namespace UKNF.Backend.Services.Communication;

public class CasesService
{
    private static readonly CaseRecord[] SeedCases =
    {
        new(
            "case-1",
            "UKNF/2025/221",
            "Late submission of quarterly report",
            "In Review",
            DateTimeOffset.Parse("2025-03-26T11:10:00Z", CultureInfo.InvariantCulture)
        ),
        new(
            "case-2",
            "UKNF/2025/198",
            "Request for additional AML documentation",
            "Awaiting Entity Response",
            DateTimeOffset.Parse("2025-03-19T09:48:00Z", CultureInfo.InvariantCulture)
        )
    };

    public IEnumerable<CaseRecord> GetAll() => SeedCases;
}
