namespace RohanSpeechApp.Interfaces
{
    public interface ISpeechSamplesProvider
    {
        public string GetRandomSample();

        public List<String> GetAllSamples();

        public List<String> GetAllSamplesFromFile(string filePath);

        public string GetSpecificSample(int index);
    }
}
