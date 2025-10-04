using Microsoft.AspNetCore.Mvc;
using UKNF.Backend.Models.Communication;
using UKNF.Backend.Services.Communication;

namespace UKNF.Backend.Controllers.Communication;

[ApiController]
[Route("api/communication/reports")]
public class ReportsController : ControllerBase
{
    private readonly ReportsService _reportsService;

    public ReportsController(ReportsService reportsService)
    {
        _reportsService = reportsService;
    }

    [HttpGet]
    public ActionResult<IEnumerable<ReportRecord>> GetReports()
    {
        return Ok(_reportsService.GetAll());
    }
}
