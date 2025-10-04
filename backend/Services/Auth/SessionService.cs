using System.Collections.Concurrent;
using UKNF.Backend.Dtos.Auth;
using UKNF.Backend.Models.Auth;

namespace UKNF.Backend.Services.Auth;

public class SessionService
{
    private readonly ConcurrentDictionary<string, ActiveSession> _sessions = new();

    public ActiveSession SelectEntity(string userId, SelectEntityDto payload)
    {
        var session = new ActiveSession(
            userId,
            payload.EntityId.Trim(),
            DateTimeOffset.UtcNow
        );

        _sessions[userId] = session;
        return session;
    }

    public ActiveSession? FindOne(string userId)
    {
        return _sessions.TryGetValue(userId, out var session) ? session : null;
    }
}
