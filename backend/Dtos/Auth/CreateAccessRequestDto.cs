using System.ComponentModel.DataAnnotations;

namespace UKNF.Backend.Dtos.Auth;

public class CreateAccessRequestDto
{
    [Required]
    [EmailAddress]
    public string Email { get; set; } = string.Empty;

    [Required]
    [MinLength(3)]
    public string EntityId { get; set; } = string.Empty;

    [Required]
    [MinLength(10)]
    public string Justification { get; set; } = string.Empty;

    public string? RequestedRole { get; set; }
}
