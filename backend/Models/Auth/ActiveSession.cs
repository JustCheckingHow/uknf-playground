namespace UKNF.Backend.Models.Auth;

public record ActiveSession(
    string UserId,
    string EntityId,
    DateTimeOffset SelectedAt
);
