using Microsoft.AspNetCore.Mvc;
using UKNF.Backend.Models.Admin;
using UKNF.Backend.Services.Admin;

namespace UKNF.Backend.Controllers.Admin;

[ApiController]
[Route("api/admin/roles")]
public class RolesController : ControllerBase
{
    private readonly RolesService _rolesService;

    public RolesController(RolesService rolesService)
    {
        _rolesService = rolesService;
    }

    [HttpGet]
    public ActionResult<IEnumerable<RoleDefinition>> GetRoles()
    {
        return Ok(_rolesService.GetAll());
    }
}
