namespace RohanSpeechApp.Interfaces
{
    public interface IAuthenticationService
    {
        Task<string> GetSavedAuthAsync();

        Task SaveAuthAsync(string pin);

        string AuthPIN { get; set; }
    }
}
