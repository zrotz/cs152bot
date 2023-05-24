from enum import Enum, auto
import discord
import re

class State(Enum):
    REPORT_START = auto()
    AWAITING_MESSAGE = auto()
    MESSAGE_IDENTIFIED = auto()
    REPORT_COMPLETE = auto()
    REPORT_COMPLETE_LOW_PIORITY = auto()
    REPORT_COMPLETE_HIGH_PRIORITY = auto()
    REPORT_VIOLENCE = auto()
    REPORT_OTHER = auto()
    VIOLENT_ORG_PER = auto()
    VIOLENT_PER = auto()
    VIOLENT_ORG = auto()
    VIOLENT_THREAT = auto()
    ASK_TO_BLOCK = auto()

class Report:
    START_KEYWORD = "report"
    CANCEL_KEYWORD = "cancel"
    HELP_KEYWORD = "help"

    def __init__(self, client):
        self.state = State.REPORT_START
        self.client = client
        self.message = None
    
    async def handle_message(self, message):
        '''
        This function makes up the meat of the user-side reporting flow. It defines how we transition between states and what 
        prompts to offer at each of those states. You're welcome to change anything you want; this skeleton is just here to
        get you started and give you a model for working with Discord. 
        '''

        if message.content == self.CANCEL_KEYWORD:
            self.state = State.REPORT_COMPLETE
            return ["Report cancelled."]
        
        if self.state == State.REPORT_START:
            reply =  "Thank you for starting the reporting process. "
            reply += "Say `help` at any time for more information.\n\n"
            reply += "Please copy paste the link to the message you want to report.\n"
            reply += "You can obtain this link by right-clicking the message and clicking `Copy Message Link`."
            self.state = State.AWAITING_MESSAGE
            return [reply]
        
        if self.state == State.AWAITING_MESSAGE:
            # Parse out the three ID strings from the message link
            m = re.search('/(\d+)/(\d+)/(\d+)', message.content)
            if not m:
                return ["I'm sorry, I couldn't read that link. Please try again or say `cancel` to cancel."]
            guild = self.client.get_guild(int(m.group(1)))
            if not guild:
                return ["I cannot accept reports of messages from guilds that I'm not in. Please have the guild owner add me to the guild and try again."]
            channel = guild.get_channel(int(m.group(2)))
            if not channel:
                return ["It seems this channel was deleted or never existed. Please try again or say `cancel` to cancel."]
            try:
                message = await channel.fetch_message(int(m.group(3)))
            except discord.errors.NotFound:
                return ["It seems this message was deleted or never existed. Please try again or say `cancel` to cancel."]

            # Here we've found the message - it's up to you to decide what to do next!
            self.state = State.MESSAGE_IDENTIFIED
            return ["I found this message:", "```" + message.author.name + ": " + message.content + "```", \
                    "What is the reason for reporting this message?  Your options are:", \
                    "`Violence or Dangerous Organization`\n`Bullying or Harassment`\n`Scam or Fraud`\n`Intellectual Property Violation`\n`Offensive Content`\n`Personal Preference`"]
        
        if self.state == State.MESSAGE_IDENTIFIED:
            if message.content.lower() != "violence or dangerous organization":
                self.state = State.REPORT_COMPLETE_LOW_PIORITY
            else:
                self.state = State.REPORT_VIOLENCE
                return ["What is the type of abuse?  Your options are:", \
                        "`Violent Threat`\n`Dangerous organization or individual`\n`Animal Abuse`\n`Death or severe injury`"]

        if self.state == State.REPORT_VIOLENCE:
            if message.content.lower() in ["animal abuse", "death or severe injury"]:
                self.state = State.REPORT_COMPLETE_LOW_PIORITY
            elif message.content.lower() == "dangerous organization or individual":
                self.state = State.VIOLENT_ORG_PER
                return ["Are you reporting an organization or an individual?\nYour options are: `organization` or `individual`"]
            elif message.content.lower() == "violent threat":
                self.state = State.VIOLENT_THREAT
                return ["Is this an imminent threat?\nYour options are: `yes` or `no`"]
            
        if self.state == State.VIOLENT_THREAT:
            self.state = State.REPORT_COMPLETE_HIGH_PRIORITY

        if self.state == State.VIOLENT_ORG_PER:
            if message.content.lower() == "individual":
                self.state = State.VIOLENT_PER
                return ["Do you suspect this individual to be an imminent threat?\nYour options are: `yes` or `no`"]
            elif message.content.lower() == "organization":
                self.state = State.VIOLENT_ORG
                return ["Do you suspect this organization to be an imminent threat?\nYour options are: `yes` or `no`"]

        if self.state == State.VIOLENT_PER:
            self.state = State.ASK_TO_BLOCK
            return ["Would you like to block this individual?\nYour options are: `yes` or `no`"]
        
        if self.state == State.VIOLENT_ORG:
            if message.content.lower() == "yes":
                self.state = State.REPORT_COMPLETE_HIGH_PRIORITY
            elif message.content.lower() == "no":
                self.state = State.REPORT_COMPLETE_LOW_PIORITY
                return ["Please select one of the following:\n`The post praises a designated entity or event`\n`The post provides and/or encourages financial support of a designated entity`\n`The post promotes the representation of a designated entity`"]

        if self.state == State.ASK_TO_BLOCK:
            self.state = State.REPORT_COMPLETE_HIGH_PRIORITY

        if self.state == State.REPORT_COMPLETE_LOW_PIORITY:
            self.state = State.REPORT_COMPLETE
            return ["Thank you for submitting a report. Our content moderation team will review the post and will decide on the appropiate action."]

        if self.state == State.REPORT_COMPLETE_HIGH_PRIORITY:
            self.state = State.REPORT_COMPLETE
            return ["Thank you for submitting a report. Our content moderation team will prioritize this post. If this is an imminent threat, please also contact your local authorities."]

        return []

    def report_complete(self):
        return self.state == State.REPORT_COMPLETE
    


    

