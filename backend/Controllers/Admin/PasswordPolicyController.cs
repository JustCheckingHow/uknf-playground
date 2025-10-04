using Microsoft.AspNetCore.Mvc;
using UKNF.Backend.Models.Admin;
using UKNF.Backend.Services.Admin;

namespace UKNF.Backend.Controllers.Admin;

[ApiController]
[Route("api/admin/password-policy")]
public class PasswordPolicyController : ControllerBase
{
    private readonly PasswordPolicyService _passwordPolicyService;

    public PasswordPolicyController(PasswordPolicyService passwordPolicyService)
    {
        _passwordPolicyService = passwordPolicyService;
    }

    [HttpGet]
    public ActionResult<PasswordPolicy> GetPolicy()
    {
        return Ok(_passwordPolicyService.GetPolicy());
    }

    [HttpPut]
    public ActionResult<PasswordPolicy> UpdatePolicy([FromBody] PasswordPolicy payload)
    {
        if (payload is null)
        {
            return BadRequest("Payload is required");
        }

        var updated = _passwordPolicyService.UpdatePolicy(payload);
        return Ok(updated);
    }
}
