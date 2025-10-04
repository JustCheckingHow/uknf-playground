using Microsoft.AspNetCore.Mvc;
using UKNF.Backend.Models.Communication;
using UKNF.Backend.Services.Communication;

namespace UKNF.Backend.Controllers.Communication;

[ApiController]
[Route("api/communication/messages")]
public class MessagesController : ControllerBase
{
    private readonly MessagesService _messagesService;

    public MessagesController(MessagesService messagesService)
    {
        _messagesService = messagesService;
    }

    [HttpGet]
    public ActionResult<IEnumerable<MessageRecord>> GetMessages()
    {
        return Ok(_messagesService.GetAll());
    }
}
