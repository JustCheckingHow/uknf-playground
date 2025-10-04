using Microsoft.AspNetCore.Mvc;
using UKNF.Backend.Models.Admin;
using UKNF.Backend.Services.Admin;

namespace UKNF.Backend.Controllers.Admin;

[ApiController]
[Route("api/admin/users")]
public class UsersController : ControllerBase
{
    private readonly UsersService _usersService;

    public UsersController(UsersService usersService)
    {
        _usersService = usersService;
    }

    [HttpGet]
    public ActionResult<IEnumerable<ManagedUser>> GetUsers()
    {
        return Ok(_usersService.GetAll());
    }
}
