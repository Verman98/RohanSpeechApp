using RohanSpeechApp.Interfaces;
using RohanSpeechApp.Models;
using System.Text.Json;

namespace RohanSpeechApp.Services
{
    public class GameService : IGameService
    {
        private readonly IVolumesRepository _volumesRepository;

        public GameData GameData { get; set; } = new();

        private int XPLEVELMULTIPLIER = 5;

        public event EventHandler<GameData> XPChangedEventHandler;
        public event EventHandler<GameData> LevelUpEventHandler;


        public GameService(IVolumesRepository _volumesRepository)
        {
            this._volumesRepository = _volumesRepository;
        }

        #region Save and Load config

        public async Task<GameData> LoadGameClassAsync()
        {
            string folderPath = _volumesRepository.GetGameConfigPath();

            if(!File.Exists(folderPath))
            {
                File.Create(folderPath).Dispose();

                await SaveGameDataAsync(GameData);
            
            } else
            {
                using FileStream fileStream = new(folderPath, FileMode.Open, FileAccess.Read);

                GameData = await JsonSerializer.DeserializeAsync<GameData>(fileStream);

            }

            GameData ??= new();

            return GameData;
        }

        public async Task SaveGameDataAsync(GameData gameData)
        {
            gameData ??= GameData;

            using FileStream fileStream = new(_volumesRepository.GetGameConfigPath(), FileMode.Create, FileAccess.ReadWrite);

            await JsonSerializer.SerializeAsync(fileStream, gameData);
        }

        #endregion


        public int GetLevelTotalXP()
        {
            if(GameData == null) return 0;

            return GameData.Level * XPLEVELMULTIPLIER;
        }

        public double GetXPPercentage()
        {
            if(GameData == null) return 0;

            return ((double)GameData.Experience / (double)GetLevelTotalXP()) * 100.0;
        }

        public async Task AddXP()
        {
            GameData.Experience++;

            if (GameData.Experience >= GetLevelTotalXP())
            {
                GameData.Level++;
                GameData.Experience = 0;
                LevelUpEventHandler?.Invoke(this, GameData);

            }

            await SaveGameDataAsync(GameData);

            XPChangedEventHandler?.Invoke(this, GameData);
        }

    }
}
