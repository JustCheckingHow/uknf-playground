using Microsoft.AspNetCore.Mvc;

namespace UKNF.Backend.Controllers;

[ApiController]
[Route("api")]
public class HealthController : ControllerBase
{
    [HttpGet("health")]
    public IActionResult Health()
    {
        var response = new
        {
            status = "ok",
            timestamp = DateTimeOffset.UtcNow
        };

        return Ok(response);
    }
}
