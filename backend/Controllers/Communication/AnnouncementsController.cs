using Microsoft.AspNetCore.Mvc;
using UKNF.Backend.Models.Communication;
using UKNF.Backend.Services.Communication;

namespace UKNF.Backend.Controllers.Communication;

[ApiController]
[Route("api/communication/announcements")]
public class AnnouncementsController : ControllerBase
{
    private readonly AnnouncementsService _announcementsService;

    public AnnouncementsController(AnnouncementsService announcementsService)
    {
        _announcementsService = announcementsService;
    }

    [HttpGet]
    public ActionResult<IEnumerable<AnnouncementRecord>> GetAnnouncements()
    {
        return Ok(_announcementsService.GetAll());
    }
}
