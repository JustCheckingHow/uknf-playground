using Microsoft.AspNetCore.Mvc;
using UKNF.Backend.Models.Communication;
using UKNF.Backend.Services.Communication;

namespace UKNF.Backend.Controllers.Communication;

[ApiController]
[Route("api/communication/entities")]
public class EntitiesController : ControllerBase
{
    private readonly EntitiesService _entitiesService;

    public EntitiesController(EntitiesService entitiesService)
    {
        _entitiesService = entitiesService;
    }

    [HttpGet]
    public ActionResult<IEnumerable<EntityRecord>> GetEntities()
    {
        return Ok(_entitiesService.GetAll());
    }
}
