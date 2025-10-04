using System.Globalization;
using UKNF.Backend.Models.Admin;

namespace UKNF.Backend.Services.Admin;

public class UsersService
{
    private static readonly ManagedUser[] SeedUsers =
    {
        new(
            "admin-1",
            "admin@uknf.gov.pl",
            "System Administrator",
            new[] { "system-admin" },
            "Active",
            DateTimeOffset.Parse("2025-03-25T07:12:00Z", CultureInfo.InvariantCulture)
        ),
        new(
            "supervisor-1",
            "supervisor@uknf.gov.pl",
            "Supervision Officer",
            new[] { "supervisor" },
            "Active",
            null
        )
    };

    public IEnumerable<ManagedUser> GetAll() => SeedUsers;
}
