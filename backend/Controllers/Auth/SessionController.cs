using Microsoft.AspNetCore.Mvc;
using UKNF.Backend.Dtos.Auth;
using UKNF.Backend.Models.Auth;
using UKNF.Backend.Services.Auth;

namespace UKNF.Backend.Controllers.Auth;

[ApiController]
[Route("api/auth/session")]
public class SessionController : ControllerBase
{
    private readonly SessionService _sessionService;

    public SessionController(SessionService sessionService)
    {
        _sessionService = sessionService;
    }

    [HttpPost("{userId}/entity")]
    public ActionResult<ActiveSession> SelectEntity(string userId, [FromBody] SelectEntityDto payload)
    {
        if (string.IsNullOrWhiteSpace(userId))
        {
            return BadRequest("User identifier is required");
        }

        var session = _sessionService.SelectEntity(userId.Trim(), payload);
        return Ok(session);
    }

    [HttpGet("{userId}")]
    public ActionResult<ActiveSession?> GetSession(string userId)
    {
        if (string.IsNullOrWhiteSpace(userId))
        {
            return BadRequest("User identifier is required");
        }

        var session = _sessionService.FindOne(userId.Trim());
        return session is null ? Ok((ActiveSession?)null) : Ok(session);
    }
}
