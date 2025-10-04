using System.ComponentModel.DataAnnotations;

namespace UKNF.Backend.Dtos.Auth;

public class RegisterUserDto
{
    [Required]
    [MinLength(1)]
    public string FirstName { get; set; } = string.Empty;

    [Required]
    [MinLength(1)]
    public string LastName { get; set; } = string.Empty;

    [Required]
    [EmailAddress]
    public string Email { get; set; } = string.Empty;

    [Required]
    [RegularExpression(@"^\+?48(?:[ -]?\d){9}$", ErrorMessage = "Phone number must be a valid Polish number")]
    public string PhoneNumber { get; set; } = string.Empty;

    [Required]
    [MinLength(12)]
    public string Password { get; set; } = string.Empty;

    [Required]
    [MinLength(3)]
    public string EntityId { get; set; } = string.Empty;
}
