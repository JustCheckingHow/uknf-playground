using System.Globalization;
using UKNF.Backend.Models.Communication;

namespace UKNF.Backend.Services.Communication;

public class EntitiesService
{
    private static readonly EntityRecord[] SeedEntities =
    {
        new(
            "ent-1",
            "Bank of Example S.A.",
            "Bank",
            "0000123456",
            DateTimeOffset.Parse("2025-03-25T00:00:00Z", CultureInfo.InvariantCulture)
        ),
        new(
            "ent-2",
            "SecurePay Payments Sp. z o.o.",
            "Payment Institution",
            "0000654321",
            DateTimeOffset.Parse("2025-02-17T00:00:00Z", CultureInfo.InvariantCulture)
        ),
        new(
            "ent-3",
            "Future Mutual Fund TFI S.A.",
            "Investment Fund Company",
            null,
            DateTimeOffset.Parse("2025-01-09T00:00:00Z", CultureInfo.InvariantCulture)
        )
    };

    public IEnumerable<EntityRecord> GetAll() => SeedEntities;
}
