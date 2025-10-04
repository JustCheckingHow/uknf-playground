namespace UKNF.Backend.Models.Admin;

public record RoleDefinition(
    string Id,
    string Name,
    string Description,
    IReadOnlyCollection<string> Permissions
);
