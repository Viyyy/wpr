import yaml

class WebConfig():
    def __init__(self, config_path='config.yml'):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
    
    @property
    def server(self):
        return self.config['server']
    
    @property
    def app(self):
        return self.config['app']
    
    @property
    def cors(self):
        return self.config['app']['cors']
    
    @property
    def api(self):
        return self.config['api']
    
    @property
    def sqlite_db(self):
        return self.config['database']['sqlite']
    
    
webConfig = WebConfig()