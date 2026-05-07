import React, { useCallback, useState } from 'react';
import Sidebar from './components/Sidebar';
import HomeContent from './components/HomeContent';
import FlightQueryModal from './components/FlightQueryModal';
import RightPanel from './components/RightPanel';
import TerminalMapView from './components/TerminalMapView';
import NavigationFlowView from './components/NavigationFlowView';
import FacilitiesDirectoryView from './components/FacilitiesDirectoryView';
import LostFoundView from './components/LostFoundView';
import ChatPanel from './components/ChatPanel';
import ChatWindow from './components/ChatWindow';
import InputBox from './components/InputBox';
import QuickActions from './components/QuickActions';
import BottomNav from './components/BottomNav';
import PlaceholderView from './components/PlaceholderView';
import CrisisContactOverlay from './components/CrisisContactOverlay';
import ReportIssueModal from './components/ReportIssueModal';
import OperationalAlertsBar from './components/OperationalAlertsBar';
import OperatorConsoleView from './components/OperatorConsoleView';
import { sendChatMessage } from './services/api';
import './styles.css';

function formatTime() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

const WELCOME = {
  text: "You're in AirHelp for CSMIA Mumbai, Terminal 2. Ask about facilities, flights, walking routes, or issues — or say e.g. “take me to BIBA”.",
  role: 'bot',
  time: formatTime(),
};

function App() {
  const [messages, setMessages] = useState([WELCOME]);
  const [isLoading, setIsLoading] = useState(false);
  const [location, setLocation] = useState('t2_entrance');
  const [chatOpen, setChatOpen] = useState(true);       // desktop chat panel open/minimized
  const [mobileView, setMobileView] = useState('home'); // 'home' | 'chat' | 'map' | 'nav' | 'facilities' | 'lostfound' | 'profile'
  const [sidebarNav, setSidebarNav] = useState('Home');
  /** When opening the floor map from walking-directions flow: `{ fromId, toId, routeIndex }`. */
  const [mapLaunch, setMapLaunch] = useState(null);
  /** After computing a route on the map, jump to Navigation with live step-by-step (`_id` disambiguates StrictMode). */
  const [guidedNavHandoff, setGuidedNavHandoff] = useState(null);
  /** Full-screen helpline / website when backend returns ``crisis_contact`` (medical, lost, disoriented). */
  const [crisisContact, setCrisisContact] = useState(null);
  const [showFlightModal, setShowFlightModal] = useState(false);
  const [reportIssueOpen, setReportIssueOpen] = useState(false);
  const showMap = sidebarNav === 'Map' || mobileView === 'map';
  const showNavFlow = sidebarNav === 'Navigation' || mobileView === 'nav';
  const showFacilities = sidebarNav === 'Facilities' || mobileView === 'facilities';
  const showLostFound = sidebarNav === 'Lost & Found' || mobileView === 'lostfound';
  const showOperator = sidebarNav === 'Operator' || mobileView === 'operator';
  const showProfilePlaceholder =
    !showMap &&
    !showNavFlow &&
    !showFacilities &&
    !showLostFound &&
    (sidebarNav === 'Profile' || mobileView === 'profile');

  const clearMapLaunch = useCallback(() => setMapLaunch(null), []);

  const clearGuidedNavHandoff = useCallback(() => {
    setGuidedNavHandoff(null);
  }, []);

  const openStepByStepFromMap = useCallback((payload) => {
    setGuidedNavHandoff({
      ...payload,
      _id: Date.now(),
    });

    setSidebarNav('Navigation');
    setMobileView('nav');
  }, []);

  /** Keep sidebar highlight and mobile full-screen view in sync when switching primary areas. */
  const handleNavSelect = useCallback((label) => {
    setSidebarNav(label);
    if (label === 'Map') setMobileView('map');
    else if (label === 'Navigation') setMobileView('nav');
    else if (label === 'Facilities') setMobileView('facilities');
    else if (label === 'Lost & Found') setMobileView('lostfound');
    else if (label === 'Operator') setMobileView('operator');
    else setMobileView('home');
  }, []);

  const handleNewChat = useCallback(() => {
    setMessages([{ ...WELCOME, time: formatTime() }]);
    setCrisisContact(null);
    handleNavSelect('Home');
    setChatOpen(true);
  }, [handleNavSelect]);

  const handleMobileViewChange = useCallback((view) => {
    setMobileView(view);
    if (view === 'map') setSidebarNav('Map');
    else if (view === 'nav') setSidebarNav('Navigation');
    else if (view === 'facilities') setSidebarNav('Facilities');
    else if (view === 'lostfound') setSidebarNav('Lost & Found');
    else if (view === 'home') setSidebarNav('Home');
    else if (view === 'profile') setSidebarNav('Profile');
    else if (view === 'operator') setSidebarNav('Operator');
    else if (view === 'chat') setSidebarNav('Home');
  }, []);

  const openFloorMap = useCallback(
    (payload) => {
      if (payload?.fromId) setLocation(payload.fromId);
      setMapLaunch(payload || null);
      handleNavSelect('Map');
    },
    [handleNavSelect],
  );

  const goToFacilityOnMap = useCallback(
    ({ graphNodeId }) => {
      openFloorMap({ fromId: location, toId: graphNodeId, routeIndex: 0 });
    },
    [location, openFloorMap],
  );

  const handleSend = async (text, loc = null, opts = {}) => {
    const currentLocation = loc ?? location;
    if (loc) setLocation(loc);
    setCrisisContact(null);

    const userMsg = { text, role: 'user', time: formatTime() };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    // Switch mobile to chat view when user sends a message
    setMobileView('chat');
    // Ensure desktop panel is open
    setChatOpen(true);

    try {
      const data = await sendChatMessage(text, currentLocation, {
        inputMode: opts.inputMode || 'text',
        whisperLang: opts.whisperLang || null,
      });
      const botText = data.message || data.response || 'Got it!';
      setMessages((prev) => [...prev, { text: botText, role: 'bot', time: formatTime() }]);

      const payload = data.data || {};
      if (payload.crisis_contact) {
        setCrisisContact({ ...payload.crisis_contact, kind: payload.special_assistance });
      }
      const navStart = payload.start;
      const navEnd = payload.end;
      const openMapForRecommendation =
        payload.open_map_after_chat &&
        (data.type === 'recommendation' || data.intent === 'recommendation');
      if (
        navStart &&
        navEnd &&
        (data.type === 'navigation' ||
          data.intent === 'navigation' ||
          openMapForRecommendation)
      ) {
        openFloorMap({ fromId: navStart, toId: navEnd, routeIndex: 0 });
      }
    } catch (err) {
      console.error('API error:', err);
      setMessages((prev) => [
        ...prev,
        { text: 'Server not responding. Please try again.', role: 'error', time: formatTime() },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickAction = ({ message, location: actionLocation }) => {
    handleSend(message, actionLocation);
  };

  const handleTicketCreated = useCallback((ticket) => {
    const lines = [
      '## Ticket created',
      '',
      `Your reference is **${ticket.ticket_id}**.`,
      '',
      `- **Issue type:** ${ticket.category_label}`,
      `- **Summary:** ${ticket.summary}`,
      '',
    ];
    if (ticket.email_notice) {
      lines.push(ticket.email_sent ? ticket.email_notice : `**Note:** ${ticket.email_notice}`);
      lines.push('');
    }
    lines.push('Keep this number if you contact airport support about this report.');
    const text = lines.join('\n');
    setMessages((prev) => [...prev, { text, role: 'bot', time: formatTime() }]);
    setChatOpen(true);
    setMobileView('chat');
  }, []);

  return (
    <div className="app-container">
      {crisisContact ? (
        <CrisisContactOverlay data={crisisContact} onDismiss={() => setCrisisContact(null)} />
      ) : null}

      <ReportIssueModal
        open={reportIssueOpen}
        onClose={() => setReportIssueOpen(false)}
        graphLocationId={location}
        onTicketCreated={handleTicketCreated}
      />

      {/* ── Left Sidebar (Desktop) ── */}
      <Sidebar activeNav={sidebarNav} onNavChange={handleNavSelect} onNewChat={handleNewChat} />

      {/* ── Main Body ── */}
      <div className="app-body">
        <OperationalAlertsBar />

        {/* Desktop Header */}
        <header className="desktop-header" role="banner">
          <div className="header-avatar" role="button" tabIndex={0} aria-label="User account">
            G
          </div>
        </header>

        {/* Mobile Header */}
        <header className="mobile-header" role="banner">
          <button
            type="button"
            className="mobile-header-menu"
            aria-label="Go to Home"
            onClick={() => handleNavSelect('Home')}
          >
            <span className="ms">menu</span>
          </button>
          <div className="mobile-header-title">
            <h1>AirHelp</h1>
            <p>CSMIA Mumbai, Terminal 2</p>
          </div>
          <button type="button" className="mobile-header-bell" aria-label="Notifications (coming soon)">
            <span className="ms">notifications</span>
          </button>
        </header>

        {/* Content area */}
        <div
          className={`content-area${showMap ? ' content-area--map' : ''}${showFacilities && !showMap && !showNavFlow ? ' content-area--facilities' : ''}${showLostFound && !showMap && !showNavFlow ? ' content-area--facilities' : ''}${showOperator ? ' content-area--facilities' : ''}`}
        >
          <main className={`main-content${mobileView === 'chat' ? ' main-content--mobile-chat' : ''}`}>
            {showMap ? (
              <TerminalMapView
                location={location}
                onLocationChange={setLocation}
                launchRoute={mapLaunch}
                onLaunchRouteConsumed={clearMapLaunch}
                onOpenStepByStepGuidance={openStepByStepFromMap}
              />
            ) : showNavFlow ? (
              <NavigationFlowView
                location={location}
                onLocationChange={setLocation}
                onOpenFloorMap={openFloorMap}
                guidedHandoff={guidedNavHandoff}
                onGuidedHandoffConsumed={clearGuidedNavHandoff}
              />
            ) : showFacilities ? (
              <FacilitiesDirectoryView location={location} onGoToFacility={goToFacilityOnMap} />
            ) : showLostFound ? (
              <LostFoundView location={location} onOpenFloorMap={openFloorMap} />
            ) : showOperator ? (
              <OperatorConsoleView onBack={() => handleNavSelect('Home')} />
            ) : showProfilePlaceholder ? (
              <PlaceholderView
                title="Profile"
                onBack={() => handleNavSelect('Home')}
                backLabel="Back to Home"
              >
                <p>Saved trips, preferences, and account tools will show here in a future update.</p>
              </PlaceholderView>
            ) : (
              <>
                <div style={mobileView !== 'home' ? { display: 'none' } : undefined} className="home-view-mobile">
                  <HomeContent
                    onSend={handleSend}
                    onOpenNavigation={() => handleNavSelect('Navigation')}
                    onOpenFloorMap={openFloorMap}
                    onOpenReportIssue={() => setReportIssueOpen(true)}
                    onOpenFlightQueries={() => setShowFlightModal(true)}
                  />
                </div>

                <FlightQueryModal
                  visible={showFlightModal}
                  onClose={() => setShowFlightModal(false)}
                  onSaved={(resp) => {
                    const botText = resp.message || 'Flight saved.';
                    setMessages((prev) => [...prev, { text: botText, role: 'bot', time: formatTime() }]);
                  }}
                />

                {mobileView === 'chat' && (
                  <div className="mobile-chat-history">
                    <div className="mobile-chat-history-inner">
                      <ChatWindow messages={messages} isLoading={isLoading} />
                    </div>
                  </div>
                )}
              </>
            )}
          </main>

          {!showMap && !showNavFlow && !showFacilities && !showLostFound && !showOperator && !showProfilePlaceholder && (
          <RightPanel />
        )}
        </div>

        {/* ── Mobile Bottom Area (fixed) ── */}
        <div className={`mobile-bottom${showOperator ? ' mobile-bottom--operator' : ''}`}>
          {mobileView === 'home' && !showOperator && (
            <QuickActions onAction={handleQuickAction} />
          )}
          {!showOperator ? <InputBox onSend={handleSend} isLoading={isLoading} /> : null}
          <BottomNav activeView={mobileView} onViewChange={handleMobileViewChange} />
        </div>
      </div>

      {/* ── Floating Chat Panel (Desktop only) ── */}
      <ChatPanel
        messages={messages}
        isLoading={isLoading}
        onSend={handleSend}
        isOpen={chatOpen}
        onToggle={() => setChatOpen((prev) => !prev)}
        onClose={() => setChatOpen(false)}
        mapMode={showMap}
      />
    </div>
  );
}

export default App;
