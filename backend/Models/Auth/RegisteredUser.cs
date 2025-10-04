namespace UKNF.Backend.Models.Auth;

public record RegisteredUser(
    string Id,
    string FirstName,
    string LastName,
    string Email,
    string EntityId,
    DateTimeOffset RegisteredAt
);
