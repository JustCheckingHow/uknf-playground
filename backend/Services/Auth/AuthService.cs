using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using UKNF.Backend.Dtos.Auth;
using UKNF.Backend.Models.Auth;

namespace UKNF.Backend.Services.Auth;

public class AuthService
{
    private readonly ConcurrentDictionary<string, RegisteredUser> _users = new(StringComparer.OrdinalIgnoreCase);
    private int _sequence;

    public RegisteredUser Register(RegisterUserDto payload)
    {
        var userId = $"user-{Interlocked.Increment(ref _sequence)}";
        var record = new RegisteredUser(
            userId,
            payload.FirstName.Trim(),
            payload.LastName.Trim(),
            payload.Email.Trim().ToLowerInvariant(),
            payload.EntityId.Trim(),
            DateTimeOffset.UtcNow
        );

        _users[record.Email] = record;
        return record;
    }

    public IReadOnlyCollection<RegisteredUser> GetAll()
    {
        return _users.Values
            .OrderBy(user => user.RegisteredAt)
            .ToArray();
    }
}
