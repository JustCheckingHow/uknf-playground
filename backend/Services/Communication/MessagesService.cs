using System.Globalization;
using UKNF.Backend.Models.Communication;

namespace UKNF.Backend.Services.Communication;

public class MessagesService
{
    private static readonly MessageRecord[] SeedMessages =
    {
        new(
            "msg-1",
            "Clarification: PSD2 reporting scope",
            "Bank of Example S.A.",
            DateTimeOffset.Parse("2025-03-14T15:20:00Z", CultureInfo.InvariantCulture)
        ),
        new(
            "msg-2",
            "Follow-up: Cyber incident notification",
            "SecurePay Payments Sp. z o.o.",
            DateTimeOffset.Parse("2025-03-10T08:05:00Z", CultureInfo.InvariantCulture)
        )
    };

    public IEnumerable<MessageRecord> GetAll() => SeedMessages;
}
