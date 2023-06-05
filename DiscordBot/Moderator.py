from enum import Enum, auto
import discord
import re

class State(Enum):
    REVIEW_START = auto()
    REVIEW_COMPLETE = auto()
    ASSESS_IMMINENT_DANGER = auto()
    ASSESS_VIOLENT_ABUSE_TYPE = auto()
    ASSESS_THREAT_ORG_PER = auto()
    DEACTIVATE_OR_WARN = auto()
    DEACTIVATE = auto()
    ASSESS_TIER = auto()
    TIER1 = auto()
    TIER2 = auto()
    

class Moderator_Review:
    MODERATORS = ["zr", "Yesenia", "gurugautham"]
    START_KEYWORD = "review"
    CANCEL_KEYWORD = "cancel"
    HELP_KEYWORD = "help"

    def __init__(self, client, reporting_user, reported_message, report_info, mod_message):
        self.state = State.REVIEW_START
        self.client = client
        self.reporting_user = reporting_user
        self.reported_message = reported_message
        self.report_info = report_info
        self.mod_message = mod_message
        self.reviewer = None


    
    async def handle_message(self, message):
        if message.content == self.mod_message.jump_url:
            self.state = State.ASSESS_IMMINENT_DANGER
            reply = f'You are reviewing this content:\n{self.reported_message.content}\n\n'
            reply += "Does this content present an imminent danger?\nYour options are: `yes` or `no`"
            return [reply]
        
        if self.state == State.ASSESS_IMMINENT_DANGER:
            if message.content.lower() == "yes":
                reply = "You are required to report this immediately to law enforcement.\n"
                reply += f'For reporting, here is a link to the post: {self.reported_message.jump_url}\n'
                reply += "This review will now be marked as closed."
                self.state = State.REVIEW_COMPLETE
                return[reply]
            elif message.content.lower() == "no":
                self.state = State.ASSESS_VIOLENT_ABUSE_TYPE
                return ["Does the report fall into the violence or dangerous organization/individual abuse?\nYour options are: `yes` or `no`"]

        if self.state == State.ASSESS_VIOLENT_ABUSE_TYPE:
            if message.content.lower() == "yes":
                self.state = State.ASSESS_THREAT_ORG_PER
                return ["Is the user reporting a violent threat or a dangerous organization/individual?\nYour options are: `Violent Threat` or `Dangerous Organization/Individual`"]
            elif message.content.lower() == "no":
                self.state = State.REVIEW_COMPLETE
                reply = "This post is not classified into the 'violence or dangerous organization/individual' abuse type and will sent to the appropriate content moderators.\n"
                reply += "SENT!\nThis review will now be marked as closed on your end."
                return [reply]

        if self.state == State.ASSESS_THREAT_ORG_PER:
            if message.content.lower() == "violent threat":
                await self.reported_message.delete()
                self.state = State.DEACTIVATE_OR_WARN
                return ["Has the account owner been notified previously for posting a violent threat?\nYour options are: `yes` or `no`"]
            elif message.content.lower() == "dangerous organization/individual":
                self.state = State.ASSESS_TIER
                return ["What tier is the organization/individual classified as?\nYour options are: `Tier 1` or `Tier 2`"]
            
        if self.state == State.ASSESS_TIER:
            if message.content.lower() == "tier 1":
                self.state = State.TIER1
                reply = "Which one of the following apply?\n"
                reply += "`The post praises a designated entity to event.`\n"
                reply += "`The post provides and/or encourages financial support of a designated entity.`\n"
                reply += "`The post promotes the representation of a designated entity.`\n"
                return [reply]
            elif message.content.lower() == "tier 2":
                self.state = State.TIER2
                reply = "Which one of the following apply?\n"
                reply += "`The post praises a designated entity to event.`\n"
                reply += "`The post provides and/or encourages financial support of a designated entity.`\n"
                reply += "`The post promotes the representation of a designated entity.`\n"
                return [reply]

        if self.state == State.TIER1:
            self.state = State.DEACTIVATE
            return ["Would you like to deactivate this account?\nYour options are: `yes` or `no`"]
        
        if self.state == State.TIER2:
            self.state = State.DEACTIVATE_OR_WARN
            return ["Has the account owner been notified previously for posting a violent threat?\nYour options are: `yes` or `no`"]

        if self.state == State.DEACTIVATE_OR_WARN:
            if message.content.lower() == "yes":
                await self.reported_message.channel.send(f'The following user has been deactivated: {self.reported_message.author.name}')
                self.state = State.REVIEW_COMPLETE
                await self.reported_message.delete()
                return ["Thank you. This review will now be marked as closed."]
            elif message.content.lower() == "no":
                await self.reported_message.author.send(f'Your post (\"{self.reported_message.content}\") violated our policies. This is a warning. Your account will be deactivated following a repeated offense.')
                self.state = State.REVIEW_COMPLETE
                await self.reported_message.delete()
                return ["Thank you. This review will now be marked as closed."]
            
        if self.state == State.DEACTIVATE:
            if message.content.lower() == "yes":
                await self.reported_message.channel.send(f'The following user has been deactivated: {self.reported_message.author.name}')
            self.state = State.REVIEW_COMPLETE
            await self.reported_message.delete()
            return ["Thank you. This review will now be marked as closed."]
        

        return []





    def review_complete(self):
        return self.state == State.REVIEW_COMPLETE