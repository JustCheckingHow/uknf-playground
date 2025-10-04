using Microsoft.AspNetCore.Mvc;
using UKNF.Backend.Models.Communication;
using UKNF.Backend.Services.Communication;

namespace UKNF.Backend.Controllers.Communication;

[ApiController]
[Route("api/communication/faq")]
public class FaqController : ControllerBase
{
    private readonly FaqService _faqService;

    public FaqController(FaqService faqService)
    {
        _faqService = faqService;
    }

    [HttpGet]
    public ActionResult<IEnumerable<FaqRecord>> GetFaqItems()
    {
        return Ok(_faqService.GetAll());
    }
}
