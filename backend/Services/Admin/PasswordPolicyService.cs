using UKNF.Backend.Models.Admin;

namespace UKNF.Backend.Services.Admin;

public class PasswordPolicyService
{
    private readonly object _syncRoot = new();

    private PasswordPolicy _policy = new()
    {
        MinLength = 12,
        RequireUppercase = true,
        RequireLowercase = true,
        RequireNumber = true,
        RequireSymbol = true,
        RotationDays = 90,
        HistoryCount = 12
    };

    public PasswordPolicy GetPolicy()
    {
        lock (_syncRoot)
        {
            return Clone(_policy);
        }
    }

    public PasswordPolicy UpdatePolicy(PasswordPolicy policy)
    {
        if (policy is null)
        {
            throw new ArgumentNullException(nameof(policy));
        }

        lock (_syncRoot)
        {
            _policy = new PasswordPolicy
            {
                MinLength = Math.Max(1, policy.MinLength),
                RequireUppercase = policy.RequireUppercase,
                RequireLowercase = policy.RequireLowercase,
                RequireNumber = policy.RequireNumber,
                RequireSymbol = policy.RequireSymbol,
                RotationDays = Math.Max(0, policy.RotationDays),
                HistoryCount = Math.Max(0, policy.HistoryCount)
            };

            return Clone(_policy);
        }
    }

    private static PasswordPolicy Clone(PasswordPolicy source) => new()
    {
        MinLength = source.MinLength,
        RequireUppercase = source.RequireUppercase,
        RequireLowercase = source.RequireLowercase,
        RequireNumber = source.RequireNumber,
        RequireSymbol = source.RequireSymbol,
        RotationDays = source.RotationDays,
        HistoryCount = source.HistoryCount
    };
}
