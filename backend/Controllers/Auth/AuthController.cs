using Microsoft.AspNetCore.Mvc;
using UKNF.Backend.Dtos.Auth;
using UKNF.Backend.Models.Auth;
using UKNF.Backend.Services.Auth;

namespace UKNF.Backend.Controllers.Auth;

[ApiController]
[Route("api/auth")]
public class AuthController : ControllerBase
{
    private readonly AuthService _authService;

    public AuthController(AuthService authService)
    {
        _authService = authService;
    }

    [HttpPost("register")]
    public ActionResult<RegisteredUser> Register([FromBody] RegisterUserDto payload)
    {
        var user = _authService.Register(payload);
        return Ok(user);
    }

    [HttpGet("users")]
    public ActionResult<IEnumerable<RegisteredUser>> GetUsers()
    {
        return Ok(_authService.GetAll());
    }
}
