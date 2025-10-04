using System.ComponentModel.DataAnnotations;

namespace UKNF.Backend.Dtos.Auth;

public class SelectEntityDto
{
    [Required]
    [MinLength(3)]
    public string EntityId { get; set; } = string.Empty;
}
