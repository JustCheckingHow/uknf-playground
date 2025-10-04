using System.Globalization;
using UKNF.Backend.Models.Communication;

namespace UKNF.Backend.Services.Communication;

public class ReportsService
{
    private static readonly ReportRecord[] SeedReports =
    {
        new(
            "rip-2025-q1",
            "RIP Reporting Package",
            "Q1 2025",
            "Validation Error",
            DateTimeOffset.Parse("2025-04-07T10:30:00Z", CultureInfo.InvariantCulture)
        ),
        new(
            "rip-2025-q2",
            "RIP Reporting Package",
            "Q2 2025",
            "Submitted",
            DateTimeOffset.Parse("2025-07-06T09:12:00Z", CultureInfo.InvariantCulture)
        ),
        new(
            "aml-annual-2024",
            "AML Annual Summary",
            "2024",
            "Validated",
            DateTimeOffset.Parse("2025-01-12T13:45:00Z", CultureInfo.InvariantCulture)
        )
    };

    public IEnumerable<ReportRecord> GetAll() => SeedReports;
}
