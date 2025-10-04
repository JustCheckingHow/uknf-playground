using Microsoft.AspNetCore.Mvc;
using UKNF.Backend.Dtos.Auth;
using UKNF.Backend.Models.Auth;
using UKNF.Backend.Services.Auth;

namespace UKNF.Backend.Controllers.Auth;

[ApiController]
[Route("api/auth/access-requests")]
public class AccessRequestsController : ControllerBase
{
    private readonly AccessRequestsService _accessRequestsService;

    public AccessRequestsController(AccessRequestsService accessRequestsService)
    {
        _accessRequestsService = accessRequestsService;
    }

    [HttpPost]
    public ActionResult<AccessRequestRecord> Create([FromBody] CreateAccessRequestDto payload)
    {
        var record = _accessRequestsService.Create(payload);
        return Ok(record);
    }

    [HttpGet]
    public ActionResult<IEnumerable<AccessRequestRecord>> GetAll()
    {
        return Ok(_accessRequestsService.GetAll());
    }
}
