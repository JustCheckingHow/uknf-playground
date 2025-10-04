using UKNF.Backend.Models.Admin;

namespace UKNF.Backend.Services.Admin;

public class RolesService
{
    private static readonly RoleDefinition[] SeedRoles =
    {
        new(
            "system-admin",
            "System Administrator",
            "Full platform administration",
            new[] { "users.manage", "roles.manage", "policies.manage" }
        ),
        new(
            "supervisor",
            "Supervisor",
            "Review submissions and coordinate cases",
            new[] { "reports.review", "cases.manage" }
        ),
        new(
            "analyst",
            "Analyst",
            "Validate reports and publish findings",
            new[] { "reports.validate" }
        )
    };

    public IEnumerable<RoleDefinition> GetAll() => SeedRoles;
}
