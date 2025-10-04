using System.Text.Json.Serialization;

namespace UKNF.Backend.Models.Auth;

[JsonConverter(typeof(JsonStringEnumConverter))]
public enum AccessRequestStatus
{
    Pending,
    Approved,
    Rejected
}

public record AccessRequestRecord(
    string Id,
    string Email,
    string EntityId,
    string Justification,
    string? RequestedRole,
    AccessRequestStatus Status,
    DateTimeOffset CreatedAt
);
