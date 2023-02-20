using RohanSpeechApp.Models;

namespace RohanSpeechApp.Interfaces
{
    public interface IGameService
    {
        GameData GameData { get; set; }

        public event EventHandler<GameData> XPChangedEventHandler;
        public event EventHandler<GameData> LevelUpEventHandler;


        Task SaveGameDataAsync(GameData gameClass);

        Task<GameData> LoadGameClassAsync();

        int GetLevelTotalXP();

        double GetXPPercentage();

        Task AddXP();

    }
}
