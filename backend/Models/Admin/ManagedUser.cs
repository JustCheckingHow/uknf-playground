namespace UKNF.Backend.Models.Admin;

public record ManagedUser(
    string Id,
    string Email,
    string DisplayName,
    IReadOnlyCollection<string> Roles,
    string Status,
    DateTimeOffset? LastLoginAt
);
