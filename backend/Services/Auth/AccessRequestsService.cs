using System.Collections.Generic;
using System.Threading;
using UKNF.Backend.Dtos.Auth;
using UKNF.Backend.Models.Auth;

namespace UKNF.Backend.Services.Auth;

public class AccessRequestsService
{
    private readonly List<AccessRequestRecord> _requests = new();
    private int _sequence;
    private readonly object _syncRoot = new();

    public AccessRequestRecord Create(CreateAccessRequestDto payload)
    {
        var record = new AccessRequestRecord(
            $"req-{Interlocked.Increment(ref _sequence)}",
            payload.Email.Trim().ToLowerInvariant(),
            payload.EntityId.Trim(),
            payload.Justification.Trim(),
            string.IsNullOrWhiteSpace(payload.RequestedRole) ? null : payload.RequestedRole.Trim(),
            AccessRequestStatus.Pending,
            DateTimeOffset.UtcNow
        );

        lock (_syncRoot)
        {
            _requests.Add(record);
        }

        return record;
    }

    public IReadOnlyCollection<AccessRequestRecord> GetAll()
    {
        lock (_syncRoot)
        {
            return _requests.ToArray();
        }
    }
}
