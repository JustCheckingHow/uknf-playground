using Microsoft.AspNetCore.Mvc;
using UKNF.Backend.Models.Communication;
using UKNF.Backend.Services.Communication;

namespace UKNF.Backend.Controllers.Communication;

[ApiController]
[Route("api/communication/library")]
public class LibraryController : ControllerBase
{
    private readonly LibraryService _libraryService;

    public LibraryController(LibraryService libraryService)
    {
        _libraryService = libraryService;
    }

    [HttpGet]
    public ActionResult<IEnumerable<LibraryRecord>> GetLibraryItems()
    {
        return Ok(_libraryService.GetAll());
    }
}
