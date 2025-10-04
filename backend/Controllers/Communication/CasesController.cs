using Microsoft.AspNetCore.Mvc;
using UKNF.Backend.Models.Communication;
using UKNF.Backend.Services.Communication;

namespace UKNF.Backend.Controllers.Communication;

[ApiController]
[Route("api/communication/cases")]
public class CasesController : ControllerBase
{
    private readonly CasesService _casesService;

    public CasesController(CasesService casesService)
    {
        _casesService = casesService;
    }

    [HttpGet]
    public ActionResult<IEnumerable<CaseRecord>> GetCases()
    {
        return Ok(_casesService.GetAll());
    }
}
