namespace UKNF.Backend.Models.Admin;

public class PasswordPolicy
{
    public int MinLength { get; set; }

    public bool RequireUppercase { get; set; }

    public bool RequireLowercase { get; set; }

    public bool RequireNumber { get; set; }

    public bool RequireSymbol { get; set; }

    public int RotationDays { get; set; }

    public int HistoryCount { get; set; }
}
